use Module::Build;
use strict;
use warnings;

my $build = Module::Build->new(
  dist_name => 'Movie-Neo4p',
  dist_abstract => 'A Perly Neo4j example app',
  dist_version_from => 'lib/MovieNeo4p.pm',
  dist_author => 'Mark A. Jensen',
  license => 'perl',
  perl => '5.010',
  config_requires => {
    'Module::Build' => 0,
  },
  build_requires => {
    'Module::Build' => 0,
    'Test::More' => 0,
    'Test::Mojo' => 0,
    'Try::Tiny' => 0,
    'List::MoreUtils' => 0
  },
  requires => {
    'Mojolicious' => '5.0',
    'REST::Neo4p' => '0.3004',
    'Try::Tiny' => 0,
    'JSON' => '2'
  },
  meta_merge => {
    resources => {
      repository => 'https://github.com/majensen/developer-resources'
    }
  }
);

$build->create_build_script;
