require 'sinatra'
require 'neo4j'
require 'models'

set :public_folder, File.dirname(__FILE__) + '/static'

Neo4j::Session.open

get '/' do
  redirect '/index.html'
end

get '/graph' do
  # find all people who has acted in a movie
  actors = Person.query_as(:p).match("p-[:ACTED_IN]->()").pluck('distinct p')
  movies = Movie.all.to_a

  nodes = actors + movies
  links = movies.map.with_index(2).to_a.map do |movie_and_index|
    index = movie_and_index[1]
    movie_and_index[0].actors.map do |a|
      {source: index, target: nodes.index(a)}
    end
  end.flatten
  #nodes_hash = nodes.map({|n {|})}
  #
  #{nodes: nodes_hash, links:links}
  ""
end