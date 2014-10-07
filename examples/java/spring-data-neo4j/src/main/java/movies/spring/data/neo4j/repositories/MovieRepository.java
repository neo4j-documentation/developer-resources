package movies.spring.data.neo4j.repositories;

import movies.spring.data.neo4j.domain.Movie;
import org.springframework.data.neo4j.annotation.Query;
import org.springframework.data.neo4j.repository.GraphRepository;
import org.springframework.data.repository.query.Param;
import org.springframework.data.rest.core.annotation.RepositoryRestResource;

import java.util.Collection;
import java.util.List;
import java.util.Map;

/**
 * @author mh
 * @since 24.07.12
 */
//@RepositoryRestResource(collectionResourceRel = "movies", path = "movies")

// tag::repository[]
public interface MovieRepository extends GraphRepository<Movie> {
    // the "0" parameter is a workaround for a bug in SDN
    Movie findByTitle(@Param("0") String title);

    Collection<Movie> findByTitleContaining(@Param("0") String title);

    @Query("MATCH (m:Movie)<-[:ACTED_IN]-(a:Person) RETURN m.title as movie, collect(a.name) as cast LIMIT {limit}")
    List<Map<String,Object>> graph(@Param("limit") int limit);
}
// end::repository[]

