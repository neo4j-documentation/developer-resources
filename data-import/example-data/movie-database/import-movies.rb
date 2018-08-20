require 'rubygems'
require 'rest-client'
require 'json'

URL = "http://api.themoviedb.org/3"
# get the api key at https://www.themoviedb.org/faq/api and set it as environment variable
KEY = ENV['THE_MOVIE_DB_KEY']


puts setup
puts "BEGIN"
[19995 , 194, 600, 601, 602, 603, 604, 605, 606, 607, 608, 609, 13, 20526, 11, 1893, 1892, 
 1894, 168, 193, 200, 157, 152, 201, 154, 12155, 58, 285, 118, 22, 392, 5255, 568, 9800, 497, 101, 120, 121, 122].each do |id|
 puts create_movie(movie(id)) 
end
puts "COMMIT"

def get(type,id)
  url = "#{URL}/#{type}/#{id}?api_key=#{KEY}&append_to_response=casts"
  res = RestClient.get url
  File.open("json/#{id}.json", 'w') {|f| f.write(res.to_str) }
  JSON.parse(res.to_str)
end

def person(id) 
  get("person",id)
end

def clean(name) 
  name.to_s.gsub(/['"]/,"")
end
def movie(id)
  parse_movie(get("movie",id),id)
end

def parse_movie(res,id)
#  puts res.inspect
  movie = [:tagline,:released,:genres].reduce({:movie_id => id}) { |r, prop| r[prop] = res[prop.to_s] if res[prop.to_s] && res[prop.to_s].length>0; r }
  movie[:title] = res["title"]
  movie[:genres] = movie[:genres].collect { |g| g["name"] }
  movie[:actors] = res["casts"]["cast"].collect { |g| { :id => g["id"], :name => clean(g["name"]) , :role => clean(g["character"]) }}
  movie[:directors] = res["casts"]["crew"].find_all {|a| a["job"]=="Director" } .collect { |g| { :id => g["id"], :name => clean(g["name"]) }}
  movie
end

def setup
  ["CREATE INDEX ON :Movie(title)",
  "CREATE INDEX ON :Movie(movie_id)",
  "CREATE INDEX ON :Person(id)",
  "CREATE INDEX ON :Person(name)",
  "CREATE INDEX ON :Genre(genre)",""].join(";\n")
end

# node auto-index for movie_id, id, name, title, genre, type
def create_movie(movie)
  props=[:movie_id, :title,:tagline,:released].find_all{ |p| movie[p] }.collect { |p| "#{p}:'#{clean(movie[p])}'" }.join(', ')
  actors = movie[:actors].collect { |a| "CREATE UNIQUE (movie)<-[:ACTS_IN {role:'#{clean(a[:role])}'}]-(:Person:Actor {id:'#{a[:id]}', name: '#{a[:name]}'})-[:PERSON]->(people) "}.join(" \n") + "\n"
  directors = movie[:directors].collect { |a| "CREATE UNIQUE (movie)<-[:DIRECTED]-(:Person:Director {id:'#{a[:id]}', name:'#{a[:name]}'})-[:PERSON]->(people) "}.join(" \n") + "\n"
  genres = movie[:genres].collect { |g| "CREATE UNIQUE (movie)-[:GENRE]->(:Genre {genre:'#{g}'})-[:GENRE]->(genres) "}.join(" \n") + "\n"
  " MERGE (genres:Genres) 
    MERGE (movies:Movies) 
    MERGE (people:People) 
    CREATE (movie:Movie {#{props}}) 
   " + genres + actors + directors + ";"
end
