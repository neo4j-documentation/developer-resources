package example.extension.movies;

import org.codehaus.jackson.map.ObjectMapper;
import org.neo4j.server.database.CypherExecutor;

import javax.ws.rs.GET;
import javax.ws.rs.Path;
import javax.ws.rs.PathParam;
import javax.ws.rs.QueryParam;
import javax.ws.rs.core.Context;
import java.io.IOException;
import java.util.Map;

@Path("/")
public class MovieResource {

    private static ObjectMapper OBJECT_MAPPER = new ObjectMapper();
    private MovieService service;

    public MovieResource(@Context CypherExecutor cypherExecutor) {
        this.service = new MovieService(cypherExecutor.getExecutionEngine());
    }

    @GET
    @Path("/search")
    public String query(@QueryParam("q") String query) throws IOException {
        Iterable<Map<String, Object>> result = service.search(query);
        return OBJECT_MAPPER.writeValueAsString(result) ;
    }

    @GET
    @Path("/graph")
    public String query(@QueryParam("limit") Integer limit) throws IOException {
        Map<String, Object> graph = service.graph(limit == null ? 100 : limit);
        return OBJECT_MAPPER.writeValueAsString(graph) ;
    }

    @GET
    @Path("/{title}")
    public String findMovie(@PathParam("title") String title) throws IOException {
        Map movie = service.findMovie(title);
        return OBJECT_MAPPER.writeValueAsString(movie) ;
    }
}
