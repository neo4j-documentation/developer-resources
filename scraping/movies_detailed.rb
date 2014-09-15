require 'open-uri'
require 'json'
require 'csv'

API_KEY = ENV['MOVIE_DB_KEY']

#http://api.themoviedb.org/3/movie/194?api_key=926d2a79e82920b62f03b1cb57e532e6&append_to_response=casts

CSV.open("all-genres.csv2", 'wb') do |f|
  f << ["MovieId", "GenreId", "GenreName"]
end

CSV.open("all-casts.csv2", 'wb') do |f|
  f << ["MovieId", "CastId", "Character", "ActorId", "ActorName", "Order"]
end

CSV.foreach("all-movies.csv", :headers => true) do  |row|
  movie_id = row[1]
  content = open("http://api.themoviedb.org/3/movie/#{movie_id}?api_key=#{API_KEY}&append_to_response=casts").read
  result = JSON.parse(content)

  p result

  CSV.open("all-genres.csv2", 'ab') do |f|
      result["genres"].each do |row|
        f << [movie_id, row["id"], row["name"]]
      end
  end

  CSV.open("all-casts.csv2", 'ab') do |f|
    result["casts"]["cast"].each do |row|
      f << [movie_id, row["cast_id"], row["character"], row["id"], row["name"], row["order"]]
    end
  end
end
