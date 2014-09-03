package example.jdbc.movies;

import example.jdbc.util.Util;

import static spark.Spark.externalStaticFileLocation;
import static spark.Spark.setPort;

/**
 * @author Michael Hunger @since 22.10.13
 */
public class MoviesServer {

    public static void main(String[] args) {
        setPort(Util.getWebPort());
        externalStaticFileLocation("src/main/webapp");
        final MovieService service = new MovieService(Util.getNeo4jUrl());
        new MovieRoutes(service).init();
    }
}
