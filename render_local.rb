#!/usr/bin/env ruby
require 'rubygems'
require 'bundler/setup'

require 'dotenv'
Dotenv.load

require 'logger'
require 'ascii_press'

LOGGER = Logger.new(STDOUT)

require './html_transformer' # Neo Tech specific

ASCIIDOC_TEMPLATES_DIR = ENV['ASCIIDOC_TEMPLATES_DIR'] || '_templates'
IMAGE_BASE_URL = ENV['IMAGE_BASE_URL'] || 'http://dev.assets.neo4j.com.s3.amazonaws.com/wp-content/uploads/' # '.'
EXAMPLES = ENV['EXAMPLES'] || 'https://github.com/neo4j-examples'
MANUAL = ENV['MANUAL'] || 'http://neo4j.com/docs/developer-manual/current'
OPSMANUAL = ENV['OPSMANUAL'] || 'http://neo4j.com/docs/operations-manual/current'
GITHUB = ENV['GITHUB'] || 'https://github.com/neo4j-contrib/developer/tree/gh-pages'
ASCIIDOC_ATTRIBUTES = %W(allow-uri-read
                         icons=font
                         linkattrs
                         source-highlighter=codemirror
                         img=#{IMAGE_BASE_URL}
                         examples=#{EXAMPLES}
                         manual=#{MANUAL}
                         opsmanual=#{OPSMANUAL}
                         github=#{GITHUB})

raise 'Usage: feed me asciidoctor files (or pass `all` to find all files)' if ARGV.empty?

adoc_file_paths = if ARGV == ['all']
  `find . -mindepth 2 -maxdepth 4 -name "*.adoc"`.split(/[\n\r]+/)
else
  ARGV
end

# AsciiPress.verify_adoc_slugs!(adoc_file_paths)

renderer = AsciiPress::Renderer.new( # after_conversion: HtmlTransformer.method(:transform),
                                    asciidoc_options: {
                                      attributes: ASCIIDOC_ATTRIBUTES,
                                      header_footer: true,
                                      safe: 0,
                                      template_dir: ASCIIDOC_TEMPLATES_DIR,
                                    })

adoc_file_paths.each do |adoc_file_path|
  dir = File.join('deploy', File.dirname(adoc_file_path))
  FileUtils.mkdir_p(dir)
  html_file_path = File.join(dir, 'index.html')

  LOGGER.info "Rendering #{adoc_file_path} to #{html_file_path}"
  File.open(html_file_path, 'w') { |f| f << renderer.render(adoc_file_path).html }
end
