class OverrideRecipientInterceptor
  def delivering_email(message)
    add_custom_headers(message)
    message.to = Rails.application.config.recipient.override.join(",")
    message.cc = nil
    message.bcc = nil
  end

  private

  def add_custom_headers(message)
    {
      'X-Override-To' => message.to,
      'X-Override-Cc' => message.cc,
      'X-Override-Bcc' => message.bcc
    }.each do |header, addresses|
      if addresses
        addresses.each do |address|
          message.header = "#{message.header}\n#{header}: #{address}"
        end
      end
    end
  end
end

Rails.application.configure do
  if ENV['RAILS_EMAIL_OVERRIDE'].present? && !Rails.env.production?
    config.action_mailer.interceptors = %w[SandboxEmailInterceptor]

    config.recipient = ActiveSupport::OrderedOptions.new
    config.recipient.override = ENV['RAILS_EMAIL_OVERRIDE'].split 
    config.action_mailer.interceptors << OverrideRecipientInterceptor.new
  end
end
