class HtmlTransformer
  def self.transform(lines)
    transformed_lines = lines.select do |line|
      line.gsub(/href="(?:\/developer\/)?(?:(?:\.\.|[a-zA-Z0-9_-]+)\/)*([^#:]+?)"/, 'href="/developer/\1"')
          .gsub(/\/developer\/+developer/, '/developer')
          .gsub(/\/developer\/+(docs|graph-academy|graphacademy|editions|download|use-cases|online-course|online-training|blog|books|hardware-sizing|support|learning-neo4j-book)/, '/\1')
    end
    return transformed_lines.join
  end
end

