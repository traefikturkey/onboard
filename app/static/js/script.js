$(document).ready(function() {
  // Get the modal elements
  const $modal = $('.modal');
  const $tabNameInput = $('#tabNameInput');
  const $columnSelect = $('#columnSelect');
  const $saveBtn = $('#saveBtn');

  // Open the modal
  function openModal(tabName='', editIndex = -1) {
    $tabNameInput.val(tabName);
    $saveBtn.off('click').on('click', function() { saveTabName(editIndex) });
    $modal.show();
  }

  // Save the tab name
  function saveTabName(editIndex) {
    const newTabName = $tabNameInput.val().trim();
    if (newTabName) {
      const tabIndex = editIndex !== -1 ? editIndex : null;

      // Make an AJAX request to the Flask route
      $.ajax({
        url: '/save_tab_name',
        type: 'POST',
        data: JSON.stringify({ 'tab_name': newTabName, 'tab_index': tabIndex }),
        contentType: 'application/json; charset=utf-8',
        dataType: 'json',
        success: function(response) {
          console.log('Tab name saved:', response.message);
          // Reload the page or update the UI as needed
        },
        error: function(xhr, status, error) {
          console.error('Error saving tab name:', error);
        }
      });
    }
    $modal.hide();
    $tabNameInput.val('');
  }

  // Close the modal when clicking outside of it
  $(window).click(function(event) {
    if (event.target === $modal[0]) {
      $modal.hide();
    }
  });

  // Add event listeners to the buttons
  $('.new-tab-btn').click(function() { openModal(); });
  $('.edit-tab-btn').click(function() { 
    active_tab = $('.tab-bar a').filter(function() { return $(this).data('current') === 'True'; }).first();
 
    openModal(active_tab.text(), active_tab.data('index')); 
  });
  
});