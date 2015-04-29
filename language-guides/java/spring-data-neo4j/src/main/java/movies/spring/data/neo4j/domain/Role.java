package movies.spring.data.neo4j.domain;


import org.springframework.data.neo4j.annotation.*;

import java.util.Collection;

@RelationshipEntity(type = "ACTED_IN")
public class Role {
    @GraphId
    Long id;
    Collection<String> roles;
    @Fetch @StartNode Person person;
    @Fetch @EndNode   Movie movie;

    public Collection<String> getRoles() {
        return roles;
    }

    public Person getPerson() {
        return person;
    }

    public Movie getMovie() {
        return movie;
    }
}
