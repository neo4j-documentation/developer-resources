package movies.spring.data.neo4j.domain;

import org.neo4j.graphdb.Direction;
import org.springframework.data.neo4j.annotation.*;

import java.util.Collection;
import java.util.HashSet;
import java.util.Set;

// tag::movie[]
@NodeEntity
public class Movie {
    @GraphId Long id;

    @Indexed(unique=true) String title;

    int released;
    String tagline;

    @Fetch @RelatedToVia(type="ACTED_IN", direction = Direction.INCOMING) Collection<Role> roles;

// end::movie[]

    public Movie() { }

    public String getTitle() {
        return title;
    }

    public int getReleased() {
        return released;
    }

    public String getTagline() {
        return tagline;
    }

    public Collection<Role> getRoles() {
        return roles;
    }
}
