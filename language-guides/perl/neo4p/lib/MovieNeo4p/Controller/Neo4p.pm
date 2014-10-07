package MovieNeo4p::Controller::Neo4p;
use Mojo::Base 'Mojolicious::Controller';
use REST::Neo4p;
use JSON;
use Try::Tiny;
use Data::Dumper;
use strict;
use warnings;

my %Q = (
  movie => REST::Neo4p::Query->new(<<MOVIE),
MATCH (movie:Movie {title:{title}})
 OPTIONAL MATCH (movie)<-[r]-(person:Person)
 RETURN movie.title as title,
       collect({name:person.name,
                job:head(split(lower(type(r)),'_')),
                role:r.roles}) as cast LIMIT 1
MOVIE

  search => REST::Neo4p::Query->new(<<SEARCH),
MATCH (movie:Movie)
 WHERE movie.title =~ {query}
 RETURN movie
SEARCH

  graph => REST::Neo4p::Query->new(<<GRAPH),
MATCH (m:Movie)<-[r:ACTED_IN]-(a:Person)
 RETURN m as movie, collect(a) as cast, collect(r) as r
GRAPH

  limit_graph => REST::Neo4p::Query->new(<<LGRAPH)
MATCH (m:Movie)<-[r:ACTED_IN]-(a:Person)
 RETURN m as movie, collect(a) as cast, collect(r) as r
 LIMIT {limit}
LGRAPH
);

$Q{movie}->{ResponseAsObjects} = $Q{search}->{ResponseAsObjects} = 0;
while ( my ($k,$v) = each %Q ) {
  $v->{RaiseError} = 1;
}

sub root {
  my $self = shift;
  $self->render_static('index.html');
}

sub movie {
  my $self = shift;
  my $title = $self->stash('title');
  unless ($title) {
    $self->render(text => "No title provided", format=>'txt', status => 400);
    return;
  }
  try {
    $Q{movie}->execute(title => $title);
    my $row = $Q{movie}->fetch;
    $Q{movie}->finish;
    if ($row) {
      $self->render(text => encode_json { title => $$row[0], cast => $$row[1] },
		    format => 'json');
    }
    else {
      $self->render(text=>'',status=>404);
    }
  } catch {
    if (ref) {
      $self->render(text => $_->message, format=>'txt',
		    status => ref =~ /Neo4p/ ? $_->code || 500 : 500);
    }
    else {
      $self->render(text => $_, format=>'txt', status => 500);
    }
  };
  return;
}

sub search {
  my $self = shift;
  my $query = $self->param('q');
  unless ($query) {
    $self->render(text => "No query provided", format=>'txt', status => 400);
    return;
  }
  try {
    $Q{search}->execute(query => "(?i).*$query.*");
    my $ret;
    while (my $row = $Q{search}->fetch) {
      delete $$row[0]->{_node};
      push @{$ret}, { movie => $$row[0] };
    }
    $Q{search}->finish;
    if ($ret) {
      $self->render( text => encode_json $ret, format => 'json' );
    }
    else {
      $self->render(text=>'',status=>404);
    }
  } catch {
    if (ref) {
      $self->render(text => $_->message, format=>'txt',
		    status => ref =~ /Neo4p/ ? $_->code || 500 : 500);
    }
    else {
      $self->render(text => $_, format=>'txt', status => 500);
    }
  }
}

sub graph {
  my $self = shift;
  my $limit = $self->param('limit');
  my $q = defined $limit ? $Q{limit_graph} : $Q{graph};
  try {
    my (@nodes,@links,@links_h);
    my (%map);
    my $i=0;
    # note that $limit is numified - otherwise JSON will interpret as string
    # leading to a Java exception at server:
    $q->execute( $limit ? {limit => $limit+0} : {} );
    while (my $row = $q->fetch) {
      foreach (@{$row->[2]}) {
	push @links, $_->start_node->id, $_->end_node->id;
      }
      unless (defined $map{${$row->[0]}}) {
	push @nodes, {title => $$row[0]->get_property('title'), label => 'movie'};
	$map{${$row->[0]}} = $i++;
      }
      foreach (@{$row->[1]}) {
	unless (defined $map{$$_}) {
	  push @nodes, { title => $_->get_property('name'), label => 'actor'};
	  $map{$$_} = $i++;
	}
      }
      1;
    }
    $q->finish;
    unless (@nodes) { # none found
      $self->render(text=>'',status => 404);
      return;
    }
    $_ = $map{$_} for @links;
    for (my $i=0; $i<@links; $i+=2) {
      push @links_h, { source => $links[$i], target => $links[$i+1] };
    }
    $self->render( text => encode_json { nodes => \@nodes, links => \@links_h },
		   format => 'json');
  } catch {
      $self->render(text => $_->message, format=>'txt',
		    status => ref =~ /Neo4p/ ? $_->code || 500 : 500);
  }
}

1;
