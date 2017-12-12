require 'rest-client'
require 'base64'

class WordPressHttpSyncer
  def initialize(hostname, username, password, post_type, renderer, options = {})
    @username = username
    @password = password
    @hostname = hostname
    @post_type = post_type
    @logger = options[:logger] || AsciiPress.logger
    @renderer = renderer || Renderer.new
    @filter_proc = options[:filter_proc] || Proc.new { true }
    @delete_not_found = options[:delete_not_found]
    @generate_tags = options[:generate_tags]
    @options = options

    all_pages = find_all_posts
    @all_pages_by_slug = all_pages.index_by { |post| post["slug"] }
    log :info, "Got #{@all_pages_by_slug.size} pages from the database"
  end

  def sync(adoc_file_paths, custom_fields = {})
    adoc_file_paths.each do |adoc_file_path|
      sync_file_path(adoc_file_path, custom_fields)
    end
  end

  private

  def sync_file_path(adoc_file_path, custom_fields = {})
    rendering = @renderer.render(adoc_file_path)

    return if !@filter_proc.call(rendering.doc)

    if !(slug = rendering.attribute_value(:slug))
      log :warn, "WARNING: COULD NOT POST DUE TO NO SLUG FOR: #{adoc_file_path}"
      return
    end

    title = rendering.title
    html = rendering.html

    log :info, "Syncing to WordPress: #{title} (slug: #{slug})"

    custom_fields_array = {}.merge('adoc_attributes' => rendering.doc.attributes.to_json).map {|k, v| {key: k, value: v} }
    content = {
                date: Time.now.strftime("%Y-%m-%dT%H:%M:%S%:z"),
                slug: slug,
                title: title,
                content: html,
                status:   @options[:post_status] || 'draft',
                meta: custom_fields_array
              }

    content[:tags] = {post_tag: rendering.tags} if @generate_tags

    user_password = "#{@username}:#{@password}"
    headers = {:Authorization => "Basic #{Base64.encode64(user_password)}"}

    if page = @all_pages_by_slug[slug]
      if page['custom_fields']
        content[:custom_fields].each do |f|
          found = page['custom_fields'].find { |field| field['key'] == f[:key] }
          f['id'] = found['id'] if found
        end
      end

      post_id = page['id'].to_i

      log :info, "Editing Post ##{post_id} on _#{@hostname}_ custom-field #{content[:meta].inspect}"

      RestClient.post "#{@hostname}/wp-json/wp/v2/#{@post_type}/#{post_id}", content, headers
    else
      log :info, "Making a new post for '#{title}' on _#{@hostname}_"

      RestClient.post "#{@hostname}/wp-json/wp/v2/#{@post_type}", content, headers
    end
  end

  def log(level, message)
      @logger.send(level, "WORDPRESS: #{message}")
  end

  def find_all_posts
    all_pages = []

    page = 1
    per_page = 100
    while true
      response =  RestClient.get "#{@hostname}/wp-json/wp/v2/#{@post_type}?per_page=#{per_page}&page=#{page}"
      total_pages = response.headers[:x_wp_totalpages].to_i

      all_pages = all_pages + JSON.parse(response.body)

      if total_pages <= page
        return all_pages
      else
        page+=1
      end
    end
  end
end
