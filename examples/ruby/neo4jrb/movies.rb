require 'sinatra'

require 'neo4j'
set :public_folder, File.dirname(__FILE__) + '/static'


class Movie
  include Neo4j::ActiveNode
  property :title
  has_many :in, :actors, origin: :ACTED_IN, rel_class: :Engagement
end

class Actor
  include Neo4j::ActiveNode
  property :name
  has_many :out, :acted_in, model_class: :Movie, type: :ACTED_IN, rel_class: :Engagement
end

class Engagement
  include Neo4j::ActiveRel
  # set_label_name:
  property :roles
end

session = Neo4j::Session.open
get '/' do
  redirect to('/index.html')
end

get '/graph' do
  query = "MATCH (m:Movie)<-[:ACTED_IN]-(a:Person) " +
  "RETURN m.title as movie, collect(a.name) as cast " +
  "LIMIT 10"

  #Movie.query_as(:m).match('<-[:ACTED_IN]-(a:Person)')
  Movie.all.each do |movie|
      puts movie.actors
  end
  ""
end