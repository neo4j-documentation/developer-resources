package example.extension.movies;

import org.apache.commons.configuration.Configuration;
import org.apache.commons.configuration.MapConfiguration;
import org.apache.commons.configuration.web.ServletConfiguration;
import org.codehaus.jackson.map.ObjectMapper;
import org.junit.*;
import org.neo4j.cypher.javacompat.ExecutionEngine;
import org.neo4j.graphdb.GraphDatabaseService;
import org.neo4j.helpers.Settings;
import org.neo4j.kernel.GraphDatabaseAPI;
import org.neo4j.kernel.configuration.Config;
import org.neo4j.kernel.logging.DevNullLoggingService;
import org.neo4j.kernel.logging.Logging;
import org.neo4j.server.CommunityNeoServer;
import org.neo4j.server.configuration.Configurator;
import org.neo4j.server.configuration.ServerConfigurator;
import org.neo4j.server.configuration.ThirdPartyJaxRsPackage;
import org.neo4j.server.database.Database;
import org.neo4j.server.database.WrappedDatabase;
import org.neo4j.server.helpers.CommunityServerBuilder;
import org.neo4j.server.preflight.PreFlightTasks;
import org.neo4j.server.rest.JaxRsResponse;
import org.neo4j.server.rest.RestRequest;
import org.neo4j.shell.ShellSettings;
import org.neo4j.test.TestGraphDatabaseFactory;

import java.util.Iterator;
import java.util.List;
import java.util.Map;

import static java.util.Arrays.asList;
import static org.junit.Assert.assertArrayEquals;
import static org.junit.Assert.assertEquals;
import static org.neo4j.helpers.collection.MapUtil.map;
import static org.neo4j.helpers.collection.MapUtil.stringMap;

@SuppressWarnings("unchecked")
public class MovieServiceIntegrationTest {

    public static final ObjectMapper OBJECT_MAPPER = new ObjectMapper();
    public static RestRequest REST_REQUEST;

    static CommunityNeoServer server;

    @BeforeClass
    public static void setUp() throws Exception {
        final GraphDatabaseAPI db = (GraphDatabaseAPI) new TestGraphDatabaseFactory().newImpermanentDatabase();

        server = new CommunityNeoServer(new ServerConfigurator(db), new Database.Factory() {
            public Database newDatabase(Config config, Logging logging) { return new WrappedDatabase(db); }
        }, DevNullLoggingService.DEV_NULL) {
            @Override
            protected PreFlightTasks createPreflightTasks() {
                return new PreFlightTasks(logging);
            }
        };
        server.getConfigurator().getThirdpartyJaxRsPackages().add(new ThirdPartyJaxRsPackage("example.extension.movies","/movie"));
        server.getConfigurator().getDatabaseTuningProperties().put(ShellSettings.remote_shell_enabled.name(), Settings.FALSE);
        System.out.println("server.baseUri() = " + server.baseUri());
        REST_REQUEST = new RestRequest(server.baseUri());
        server.start();
        createData();
        while (REST_REQUEST.get("/").getStatus() != 200) {
            System.out.println(REST_REQUEST.get("/").getStatus());
            Thread.sleep(500);
        }
    }

    private static void createData() {
        GraphDatabaseAPI db = server.getDatabase().getGraph();
        ExecutionEngine executionEngine = new ExecutionEngine(db);
        String query = "CREATE (:Movie {title:'The Matrix', released: 1999, tagline: 'The one and only'})" +
                " <-[:ACTED_IN {roles:['Neo']}]-" +
                " (:Person {name:'Keanu Reeves',born:1964})";

        executionEngine.execute(query).dumpToString();
    }

    @AfterClass
    public static void tearDown() throws Exception {
        server.stop();
    }

    @Test
    public void testFindMovie() throws Exception {
        JaxRsResponse response = REST_REQUEST.get("/movie/The%20Matrix");
        assertEquals(200, response.getStatus());
        Map movie = OBJECT_MAPPER.readValue(response.getEntity(), Map.class);
        assertEquals("The Matrix", movie.get("title"));
        List<Map> cast = (List<Map>) movie.get("cast");
        assertEquals(1, cast.size());
        Map entry = cast.get(0);
        assertEquals("Keanu Reeves", entry.get("name"));
        assertEquals("acted", entry.get("job"));
        assertArrayEquals(new String[]{"Neo"}, (String[]) entry.get("role"));
    }

    @Test
    public void testSearch() throws Exception {
        JaxRsResponse response = REST_REQUEST.get("/movie/search?q=matr");
        assertEquals(200, response.getStatus());
        List<Map<String, Object>> result = OBJECT_MAPPER.readValue(response.getEntity(), List.class);
        Map<String, Object> movie = (Map<String, Object>) result.get(0).get("movie");
        assertEquals("The Matrix", movie.get("title"));
        assertEquals(1999L, movie.get("released"));
        assertEquals("The one and only", movie.get("tagline"));
    }

    @Test
    public void testGraph() throws Exception {
        JaxRsResponse response = REST_REQUEST.get("/movie/graph?limit=10");
        assertEquals(200, response.getStatus());
        Map<String, List<Map<String, Object>>> graph = OBJECT_MAPPER.readValue(response.getEntity(), Map.class);
        List<Map<String, Object>> nodes = graph.get("nodes");
        assertEquals(asList(map("label", "movie", "title", "The Matrix"), map("label", "actor", "title", "Keanu Reeves")), nodes);
        List<Map<String, Object>> links = graph.get("links");
        assertEquals(asList(map("source", 1, "target", 0)), links);
    }
}
