
class Movie
  include Neo4j::ActiveNode
  id_property :title
  property :released
  property :tagline
  has_many :in, :actors, model_class: :Person, type: :ACTED_IN
  has_many :in, :directors, model_class: :Person, type: :DIRECTED
end

class Person
  include Neo4j::ActiveNode
  id_property :name
  has_many :out, :acted_in, model_class: :Movie, type: :ACTED_IN
  has_many :out, :directed, model_class: :Movie, type: :DIRECTED
end

