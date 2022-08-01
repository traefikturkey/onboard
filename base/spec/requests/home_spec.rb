require 'rails_helper'

RSpec.describe "Root", type: :request  do
  describe "GET root" do
    it "returns a success response" do
      get '/'
      expect(response).to have_http_status(:ok)
    end
  end
end
