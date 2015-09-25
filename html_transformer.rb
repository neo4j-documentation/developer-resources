class HtmlTransformer
  def self.transform(lines)
    transformed_lines = lines.map do |line|
      line.gsub(%r{href="(?:/developer/)? # base of the url
                  (?:(?:\.\.|[a-zA-Z0-9_-]+)/)*  # the classification that we want to bin
                  ([^#:]+?)"}x,'href="/developer/\1"')
          .gsub(/\/developer\/+developer/, '/developer')
          .gsub(/\/developer\/+(docs|graph-academy|graphacademy|editions|download|use-cases|online-course|online-training|blog|books|hardware-sizing|support|learning-neo4j-book)/, '/\1')
    end
    return transformed_lines.join("\n")
  end
end

