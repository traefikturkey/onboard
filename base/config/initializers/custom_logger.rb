class Logger::SimpleFormatter
  def call(severity, time, progname, msg)
    t = time.strftime("%Y-%m-%d %H:%M:%S.") << time.usec.to_s[0..2].rjust(3)
    "#{t} [#{severity.ljust(5, ' ')}] #{msg}\n"
  end

  def self.sql_logging(start_time, end_time, payload)
    payload_name = payload[:name]
    if !["SCHEMA", "EXPLAIN"].include?(payload_name)
      ms = ((end_time - start_time)*1000).round(1)
      payload_sql = payload[:sql].dup  # the payload is frozen
      @@long_time ||= ms + ENV.fetch("RAILS_LOG_SQL_LONG_TIME", '50').to_i if payload_name == "SQL" && payload_sql.start_with?("USE [")
      if (@@long_time && ms > @@long_time) || !ActiveModel::Type::Boolean.new.cast( ENV.fetch("RAILS_LOG_SQL_LONG_ONLY", "false") )
        duration = "(#{ms}ms)"
        if @@long_time && ms > @@long_time
          duration = duration.bold_red
        else
          duration = duration.bold_magenta
        end

        ar_call = !payload_name.to_s.blank?
        if payload_name == "SQL"
          payload_name = payload_name.to_s.strip.bold_magenta
        else
          payload_name = payload_name.to_s.strip.bold_cyan
        end

        Rails.logger.debug { "#{duration} #{payload_name}" }

        if !payload_sql.include?("\n")
          ar_call = true
          payload_sql.gsub!("EXEC sp_executesql N'", "")
          payload_sql["SELECT"] = "select" if payload_sql.start_with?('SELECT')
          payload_sql.gsub!(" FROM ", "\nfrom ")
          payload_sql.gsub!(" WHERE ", "\nwhere ")
          payload_sql.gsub!(" ORDER BY ", "\norder by ")
          payload_sql.gsub!(" GROUP BY ", "\ngroup by ")
          payload_sql.gsub!(" OFFSET", "\nOFFSET")
          payload_sql.gsub!("', N'@0", "\nN'@0")
        end

        add = ''
        remove = 0
        payload_sql.to_s.split("\n").each_with_index { |str, i|
          if i == 0
            add = ''
            remove = str[/\A */].size
            if remove < 3       # we need to add some spaces to get upto 3
              add = ' ' * (3 - remove)
              remove = 0
            else
              remove = remove - 3  # leave 3 spaces at the begining
            end
          end
          msg = str.sub(/\A {0,#{remove}}/, add).to_s
          if ar_call
            puts msg.bold_cyan
          else
            puts msg.bold_blue
          end
        }
      end
    end
  end
end

class String
  # colorization
  def colorize(color_code, bold = false)
    "#{bold ? "\e[1m" : ''}\e[#{color_code}m#{self}\e[0m"
  end

  def red
    colorize(31)
  end

  def green
    colorize(32)
  end

  def yellow
    colorize(33)
  end

  def blue
    colorize(34)
  end

  def pink
    colorize(35)
  end

  def light_blue
    colorize(36)
  end

  def magenta
    colorize(35)
  end

  def cyan
    colorize(36)
  end

  def white
    colorize(37)
  end

  def bold_red
    colorize(31, true)
  end

  def bold_green
    colorize(32, true)
  end

  def bold_yellow
    colorize(33, true)
  end

  def bold_blue
    colorize(34, true)
  end

  def bold_pink
    colorize(35, true)
  end

  def bold_light_blue
    colorize(36, true)
  end

  def bold_magenta
    colorize(35, true)
  end

  def bold_cyan
    colorize(36, true)
  end

  def bold_white
    colorize(37, true)
  end
end

Rails.application.configure do

  $stdout.sync = true

  logger = ActiveSupport::Logger.new(STDOUT)
  logger.level = Logger.const_get( ENV.fetch("RAILS_LOG_LEVEL", "DEBUG") )
  logger.formatter = Logger::SimpleFormatter.new

  config.log_tags = [:remote_ip]

  if ActiveModel::Type::Boolean.new.cast( ENV.fetch("RAILS_LOGRAGE_ENABLED", "true") )
    config.lograge.enabled = true
    config.lograge.logger = logger
    config.lograge.ignore_actions = ['HealthcheckController#index']
    config.lograge.formatter = lambda do |data|
      status = data[:status].to_s
      status = (status.start_with?('2') || status.start_with?('3')) ? status.light_blue : status.pink

      output = []
      output << "#{data[:method]}".green
      output << " #{data[:user]}".green if data[:user]
      output << " code=#{status.light_blue}".green
      output << " fmt=".green + data[:format].to_s.light_blue
      output << " time=".green + (data[:duration] || 0).to_s.light_blue
      output << " view=".green + (data[:view] || 0).to_s.light_blue
      output << " db=".green + (data[:db] || 0).to_s.light_blue
      output << " #{data[:path]}".light_blue
      output << " params=".green + data[:params].to_s.light_blue

      output.join.to_s
    end
    config.lograge.custom_options = lambda do |event|
      # capture parameters
      unwanted_keys = %w[format action controller utf8 authenticity_token]
      params = event.payload[:params].reject { |key,_| unwanted_keys.include? key }

      {
        :params => params,
        :ip => event.payload[:headers][:REMOTE_ADDR],
        :user => event.payload[:user]
      }
    end

    Rails.logger = logger
    log_type = "lograge".pink
  else
    Rails.logger = logger
    log_type = "standard".red
  end

  if ActiveModel::Type::Boolean.new.cast( ENV.fetch("RAILS_LOG_SQL", "false") )
    ActiveSupport::Notifications.subscribe('sql.active_record') do |_, start_time, end_time, _, payload|
      Logger::SimpleFormatter.sql_logging(start_time, end_time, payload)
    end

    sql_logging = "enabled".green
  else
    sql_logging = "disabled".red
  end

  if ActiveModel::Type::Boolean.new.cast( ENV.fetch("RAILS_LOG_SQL_CALLERS", "false") )
    sql_callers = "enabled".green
  else
    sql_callers = "disabled".red
  end

  rail_log_message = "RAILS_ENV: ".light_blue
  rail_log_message << Rails.env.red
  rail_log_message << " LOG[#{log_type}]: ".light_blue
  rail_log_message << ENV.fetch("RAILS_LOG_LEVEL", "DEBUG".downcase).red
  

  sql_log_message = "SQL logging: ".light_blue
  sql_log_message << sql_logging
  sql_log_message << " SQL callers: ".light_blue
  sql_log_message << sql_callers

  unless Rails.env.test? 
    Rails.logger.info rail_log_message 
    Rails.logger.info sql_log_message 
    Rails.logger.info "Site URL: ".light_blue + "https://#{ENV['APP_FQDN']}/".green 
  end
end