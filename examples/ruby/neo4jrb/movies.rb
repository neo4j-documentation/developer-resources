require 'sinatra'
require 'neo4j'
require 'models'

set :public_folder, File.dirname(__FILE__) + '/static'

Neo4j::Session.open

get '/' do
  redirect '/index.html'
end

get '/graph' do
  actors = Person.all.to_a # or if we want to be sure, query_as(:p).match("p-[:ACTED_IN]->()").pluck('distinct p')
  movies = Movie.all.to_a

  nodes = actors + movies
  links = movies.map.with_index(2).to_a.map do |movie_and_index|
    movie_and_index[0].actors.map do |a|
      {source: movie_and_index[1], target: nodes.index(a)}
    end
  end.flatten

  nodes_hash = actors.map{|n| {title: n.name, label: "actor"}} + movies.map{|n| {title: n.title, label: "movie"}}

  {nodes: nodes_hash, links:links}
end