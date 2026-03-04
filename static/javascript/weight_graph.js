(function () {
  var ctx = document.getElementById("weightChart");
  if (!ctx || !weightsData || weightsData.length === 0) return;

  var months = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];

  new Chart(ctx, {
    type: "line",
    data: {
      labels: weightsData.map(function (item) {
        var parts = item.date.split("-");
        return months[parseInt(parts[1]) - 1] + " " + parseInt(parts[2]);
      }),
      datasets: [{
        data: weightsData.map(function (item) { return item.weight; }),
        tension: 0.25,
        pointRadius: 3,
        borderColor: "#57068c",
        backgroundColor: "rgba(87, 6, 140, 0.08)",
        fill: true,
      }],
    },
    options: {
      plugins: { legend: { display: false } },
      scales: {
        x: { ticks: { maxTicksLimit: 8 } },
        y: { title: { display: true, text: "kg" } },
      },
    },
  });
})();
