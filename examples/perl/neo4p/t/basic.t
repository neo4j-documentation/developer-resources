use Mojo::Base -strict;
use lib '../lib';
use Test::More;
use Test::Mojo;
use List::MoreUtils qw/uniq/;
use Try::Tiny;

use_ok('MovieNeo4p');
use_ok('MovieNeo4p::Controller::Neo4p');
my $t;
my $neo4j_available = 1;
try {
 $t = Test::Mojo->new('MovieNeo4p');
} catch {
  $neo4j_available = 0;
  fail $_;
  done_testing;
};

SKIP : {
  skip 'Neo4j server not available, skipping tests', 1 unless $neo4j_available;
  $t->get_ok('/')->status_is(200)->content_like(qr/World's Leading Graph Database/);
  $t->get_ok('/movie')->status_is(400);
  $t->get_ok('/search')->status_is(400);
  $t->get_ok('/movie/The Matrix')->status_is(200)->header_is('Content-Type' => 'application/json')->json_has('/title')->json_has('/cast');
  $t->get_ok('/movie/The%20Matrix')->status_is(200)->header_is('Content-Type' => 'application/json')->json_has('/title')->json_has('/cast');
  $t->get_ok('/search?q=matrix')->status_is(200)->header_is('Content-Type' => 'application/json')->json_has('/0/movie/released')->json_has('/0/movie/tagline')->json_has('/0/movie/title');
  $t->get_ok('/graph?limit=20')->status_is(200)->header_is('Content-Type' => 'application/json');
  $t->get_ok('/graph')->status_is(200)->header_is('Content-Type' => 'application/json');
  my $j = $t->tx->res->json;
  my $tom;
  for (@{$j->{nodes}}) {
    $tom++;
    if (($_->{title} =~ /Tom Hanks/) &&
	  ($_->{label} =~ /actor/) ) {
      last;
    }
  }
  fail 'Tom Hanks not found from /graph endpt' unless $tom < @{$j->{nodes}};
  --$tom;
  my @tom_movies = grep { $_->{source} == $tom } @{$j->{links}};
  @tom_movies = map { $_->{target} } @tom_movies;
  @tom_movies = @{$j->{nodes}}[@tom_movies];
  @tom_movies = sort map { $_->{title} } @tom_movies;
  my $q = REST::Neo4p::Query->new(<<QUERY);
MATCH (a:Person)-[:ACTED_IN]->(m:Movie) 
 WHERE a.name = 'Tom Hanks'
 RETURN m.title
QUERY
  $q->execute;
  fail $q->errstr if $q->err;
  my @from_db;
  while (my $row = $q->fetch) {
    push @from_db, $$row[0];
  }
  is_deeply [sort @from_db], \@tom_movies, 'Tom Hanks movies correctly retrieved in D3 graph description format';
  1;
}



done_testing();
