package movies.spring.data.neo4j.domain;

import org.springframework.data.neo4j.annotation.GraphId;
import org.springframework.data.neo4j.annotation.Indexed;
import org.springframework.data.neo4j.annotation.NodeEntity;
import org.springframework.data.neo4j.annotation.RelatedTo;

import java.util.Collection;

@NodeEntity
public class Person {
    @GraphId Long id;

    @Indexed private String name;
    private int born;

    @RelatedTo(type = "ACTED_IN")
    Collection<Movie> movies;

    public Person() { }

    public String getName() {
        return name;
    }

    public int getBorn() {
        return born;
    }

    public Collection<Movie> getMovies() {
        return movies;
    }
}
