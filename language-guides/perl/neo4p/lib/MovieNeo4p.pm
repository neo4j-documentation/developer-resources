package MovieNeo4p;
use Mojo::Base 'Mojolicious';
use REST::Neo4p;
use Try::Tiny;

BEGIN {
  $MovieNeo4p::VERSION='0.01';
}
# This method will run once at server start
sub startup {
  my $self = shift;
  $self->secrets(['furshlugginer','cowznofski']);
  $self->config( hypnotoad => {
    listen => ['http://*:3000'],
  });

  try {
    REST::Neo4p->connect($ENV{NEO4J_URL} || 'http://127.0.0.1:7474');
  } catch {
    ref $_ ? $_->can('rethrow') && $_->rethrow || die $_->message : die $_;
  };


  # Router
  my $r = $self->routes;
  # Normal route to controller
  $r->get('/')->to('neo4p#root');
  $r->get('/movie')->to('neo4p#movie');
  $r->get('/search')->to('neo4p#search');
  $r->get('/graph')->to('neo4p#graph');
  $r->get('/movie/:title')->to('neo4p#movie');
}

1;
