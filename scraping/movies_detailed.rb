require 'open-uri'
require 'json'
require 'csv'

API_KEY = ENV['MOVIE_DB_KEY']

CSV.open("all-genres.csv", 'wb') do |f|
  f << ["MovieId", "GenreId", "GenreName"]
end

CSV.open("all-casts.csv", 'wb') do |f|
  f << ["MovieId", "CastId", "Character", "ActorId", "ActorName", "Order"]
end

CSV.foreach("all-movies.csv", :headers => true) do  |row|
  movie_id = row[1]
  content = open("http://api.themoviedb.org/3/movie/#{movie_id}?api_key=#{API_KEY}&append_to_response=casts").read
  result = JSON.parse(content)

  CSV.open("all-genres.csv", 'ab') do |f|
      result["genres"].each do |row|
        f << [movie_id, row["id"], row["name"]]
      end
  end

  CSV.open("all-casts.csv", 'ab') do |f|
    result["casts"]["cast"].each do |row|
      f << [movie_id, row["cast_id"], row["character"], row["id"], row["name"], row["order"]]
    end
  end
end
