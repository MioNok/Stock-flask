// Call the dataTables jQuery plugin
$(document).ready(function() {
  $('#dataTable').DataTable().page.len(2).draw();
});
