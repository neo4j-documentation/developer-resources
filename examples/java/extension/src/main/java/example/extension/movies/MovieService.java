package example.extension.movies;

import org.neo4j.cypher.javacompat.ExecutionEngine;
import org.neo4j.cypher.javacompat.ExecutionResult;
import org.neo4j.graphdb.Node;
import org.neo4j.graphdb.PropertyContainer;
import org.neo4j.helpers.collection.IterableWrapper;
import org.neo4j.helpers.collection.IteratorUtil;

import java.util.*;

import static org.neo4j.helpers.collection.MapUtil.map;

public class MovieService {

    private final ExecutionEngine cypher;

    public MovieService(ExecutionEngine executionEngine) {
        cypher = executionEngine;
    }

    public Map findMovie(String title) {
        if (title==null) return Collections.emptyMap();
        return IteratorUtil.singleOrNull(cypher.execute(
                "MATCH (movie:Movie {title:{title}})" +
                        " OPTIONAL MATCH (movie)<-[r]-(person:Person)\n" +
                        " RETURN movie.title as title, collect({name:person.name, job:head(split(lower(type(r)),'_')), role:r.roles}) as cast LIMIT 1",
                map("title", title)));
    }

    @SuppressWarnings("unchecked")
    public Iterable<Map<String,Object>> search(String query) {
        if (query==null || query.trim().isEmpty()) return Collections.emptyList();
        ExecutionResult executionResult = cypher.execute(
                "MATCH (movie:Movie)\n" +
                        " WHERE movie.title =~ {query}\n" +
                        " RETURN {title:movie.title,released:movie.released,tagline:movie.tagline} as movie",
                map("query", "(?i).*" + query + ".*"));

        return IteratorUtil.asCollection(executionResult);
    }

    private Map<String,Object> toMap(PropertyContainer pc) {
        Map<String,Object> result = new LinkedHashMap<>();
        for (String prop : pc.getPropertyKeys()) {
            result.put(prop,pc.getProperty(prop));
        }
        return result;
    }
    @SuppressWarnings("unchecked")
    public Map<String, Object> graph(int limit) {
        Iterator<Map<String,Object>> result = cypher.execute(
                "MATCH (m:Movie)<-[:ACTED_IN]-(a:Person) " +
                " RETURN m.title as movie, collect(a.name) as cast " +
                " LIMIT {1}", map("1",limit)).iterator();
        List nodes = new ArrayList();
        List rels= new ArrayList();
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
}
