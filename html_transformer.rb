module HtmlTransformer
  def self.transform(lines)
    lines = lines.each_line.to_a if lines.is_a?(String)

    lines.map do |line|
      line
          .gsub(%r{/developer/+developer}, '/developer')
          .gsub(%r{/developer/+(docs|graph-academy|sandbox|graphacademy|editions|download|use-cases|online-course|online-training|blog|books|hardware-sizing|support|learning-neo4j-book)}, '/\1')
#          .gsub(%r{href="/developer/}, 'href="/developer/')
#          .gsub(%r{href="(?:/developer/)? # base of the url
#                  (?:(?:\.\.|[a-zA-Z0-9_-]+)/)*  # the classification that we want to bin
#                  ([^#:]+?)"}x,'href="/developer/\1"')
    end.join("")
  end
end

