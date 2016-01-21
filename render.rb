#!/usr/bin/env ruby
require 'rubygems'
require 'bundler/setup'
require 'logger'
require 'pathname'

require_relative 'ascii_press'
require_relative 'html_transformer' # Neo Tech specific

IMAGE_BASE_URL = 'http://dev.assets.neo4j.com.s3.amazonaws.com/wp-content/uploads/'
GITHUB = 'https://github.com/neo4j-contrib/developer-resources/tree/gh-pages'
MANUAL = 'http://neo4j.com/docs/stable'
EXAMPLES = 'https://github.com/neo4j-examples'

ASCIIDOC_TEMPLATES_DIR = ENV['ASCIIDOC_TEMPLATES_DIR'] || '_templates'
ASCIIDOC_ATTRIBUTES = %W(allow-uri-read
                         linkattrs
                         source-highlighter=codemirror
                         img=#{IMAGE_BASE_URL}
                         examples=#{EXAMPLES}
                         manual=#{MANUAL}
                         github=#{GITHUB})

raise 'Usage: feed me asciidoctor files (or pass `all` to find all files)' if ARGV.empty?

logger = Logger.new(STDOUT)
renderer = AsciiPress::Renderer.new(attributes: ASCIIDOC_ATTRIBUTES, header_footer: true, safe: 0, template_dir: ASCIIDOC_TEMPLATES_DIR)

if ENV['BLOG_HOSTNAME'] && ENV['BLOG_USERNAME'] && ENV['BLOG_PASSWORD']
  syncer = AsciiPress::WordPressSyncer.new(ENV['BLOG_HOSTNAME'], ENV['BLOG_USERNAME'], ENV['BLOG_PASSWORD'], logger: logger)
end

adoc_file_paths = if ARGV == ['all']
  `find . -mindepth 2 -maxdepth 4 -name "*.adoc"`.split(/[\n\r]+/)
else
  ARGV
end

adoc_file_paths.each do |adoc_file_path|
  rendering = renderer.render(adoc_file_path)

  if syncer
    post_name = File.basename(adoc_file_path, '.*')
    optional_slug = rendering.doc.attributes['slug'].to_s
    post_name = optional_slug unless optional_slug.empty?

    logger.info "publishing: #{rendering.doc.doctitle} (post_name: #{post_name})"

    # logger.info "data: #{rendering.data.inspect}"

    syncer.sync(rendering.doc.doctitle, post_name, rendering.html,
                [{key: 'developer_section_name', value: rendering.data[:developer_section_name]},
                 {key: 'developer_section_slug', value: ''}]) # was data[:developer_section_slug]
  else
    html_file_path = File.join(File.dirname(adoc_file_path), 'index.html')

    logger.info "Rendering #{adoc_file_path} to #{html_file_path}"
    File.open(html_file_path, 'w') { |f| f << rendering.html }
  end
end

