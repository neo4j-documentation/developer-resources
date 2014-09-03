package example.jdbc.movies;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import spark.Request;
import spark.Response;
import spark.Route;
import spark.servlet.SparkApplication;

import java.net.URI;
import java.net.URLDecoder;

import static spark.Spark.get;

public class MovieRoutes implements SparkApplication {

    private Gson gson = new GsonBuilder().disableHtmlEscaping().create();
    private MovieService service;

    public MovieRoutes(MovieService service) {
        this.service = service;
    }

    public void init() {
        get(new Route("/movie/:title") {
            public Object handle(Request request, Response response) {
                return gson.toJson(service.findMovie(URLDecoder.decode(request.params("title"))));
            }
        });
        get(new Route("/search") {
            public Object handle(Request request, Response response) {
                return gson.toJson(service.search(request.queryParams("q")));
            }
        });
        get(new Route("/graph") {
            public Object handle(Request request, Response response) {
                int limit = request.queryParams("limit") != null ? Integer.valueOf(request.queryParams("limit")) : 100;
                return gson.toJson(service.graph(limit));
            }
        });
    }
}
