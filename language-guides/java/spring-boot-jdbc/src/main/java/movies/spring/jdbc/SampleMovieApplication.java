package movies.spring.jdbc;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.autoconfigure.EnableAutoConfiguration;
import org.springframework.boot.builder.SpringApplicationBuilder;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.ComponentScan;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.core.RowMapper;
import org.springframework.jdbc.datasource.DriverManagerDataSource;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurerAdapter;

import javax.sql.DataSource;
import java.io.PrintStream;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.*;

@EnableAutoConfiguration
@ComponentScan
@RestController("/")
public class SampleMovieApplication extends WebMvcConfigurerAdapter {
    
    public static final String NEO4J_URL = System.getProperty("NEO4J_URL","jdbc:neo4j://localhost:7474");
    // neo4j 2.2 requires username and password. Default values are neo4j/neo4j
    public static final String NEO4J_USER = System.getProperty("NEO4J_USER","neo4j");
    public static final String NEO4J_PASSWORD = System.getProperty("NEO4J_PASSWORD","neo4j");

    public static final RowMapper<Movie> MOVIE_ROW_MAPPER = new RowMapper<Movie>() {
        public Movie mapRow(ResultSet rs, int rowNum) throws SQLException {
            return new Movie(rs.getString("title"),rs.getInt("released"),rs.getString("tagline"));
        }
    };

// tag::jdbctemplate[]
    @Autowired
    JdbcTemplate template;

    String GET_MOVIE_QUERY =
            "MATCH (movie:Movie {title:{1}})" +
            " OPTIONAL MATCH (movie)<-[r]-(person:Person)\n" +
            " RETURN movie.title as title, collect({name:person.name, job:head(split(lower(type(r)),'_')), role:r.roles}) as cast LIMIT 1";

    @RequestMapping("/movie/{title}")
    public Map<String,Object> movie(@PathVariable("title") String title) {
        return template.queryForMap(GET_MOVIE_QUERY, title);
    }
// end::jdbctemplate[]

    public static class Movie {
        public String title;
        public int released;
        public String tagline;

        public Movie(String title, int released, String tagline) {
            this.title = title;
            this.released = released;
            this.tagline = tagline;
        }
    }

    String SEARCH_MOVIES_QUERY =
            " MATCH (movie:Movie)\n" +
            " WHERE movie.title =~ {1}\n" +
            " RETURN movie.title as title, movie.released as released, movie.tagline as tagline";

    @RequestMapping("/search")
    public List<Movie> search(@RequestParam("q") String query) {
        if (query==null || query.trim().isEmpty()) return Collections.emptyList();
        String queryParam = "(?i).*" + query + ".*";
        return template.query(SEARCH_MOVIES_QUERY, MOVIE_ROW_MAPPER, queryParam);
    }

    public static final String GRAPH_QUERY = "MATCH (m:Movie)<-[:ACTED_IN]-(a:Person) " +
            " RETURN m.title as movie, collect(a.name) as cast " +
            " LIMIT {1}";

    @RequestMapping("/graph")
    public Map<String, Object> graph(@RequestParam(value = "limit",required = false) Integer limit) {
        Iterator<Map<String, Object>> result = template.queryForList(
                GRAPH_QUERY, limit == null ? 100 : limit).iterator();
        return toD3Format(result);
    }

    private Map<String, Object> toD3Format(Iterator<Map<String, Object>> result) {
        List<Map<String,Object>> nodes = new ArrayList<Map<String,Object>>();
        List<Map<String,Object>> rels= new ArrayList<Map<String,Object>>();
        int i=0;
        while (result.hasNext()) {
            Map<String, Object> row = result.next();
            nodes.add(map("title",row.get("movie"),"label","movie"));
            int target=i;
            i++;
            for (Object name : (Collection) row.get("cast")) {
                Map<String, Object> actor = map("title", name,"label","actor");
                int source = nodes.indexOf(actor);
                if (source == -1) {
                    nodes.add(actor);
                    source = i++;
                }
                rels.add(map("source",source,"target",target));
            }
        }
        return map("nodes", nodes, "links", rels);
    }

    private Map<String, Object> map(String key1, Object value1, String key2, Object value2) {
        Map<String, Object> result = new HashMap<String,Object>(2);
        result.put(key1,value1);
        result.put(key2,value2);
        return result;
    }

    public static void main(String[] args) throws Exception {
        System.setErr(new PrintStream(System.out) {
            @Override
            public void write(int b) {
                super.write(b);
            }

            @Override
            public void write(byte[] buf, int off, int len) {
                super.write(buf, off, len);
            }
        });
        new SpringApplicationBuilder(SampleMovieApplication.class).run(args);
    }

    @Bean
    public DataSource dataSource() {
        return new DriverManagerDataSource(NEO4J_URL, NEO4J_USER, NEO4J_PASSWORD);
    }

}
