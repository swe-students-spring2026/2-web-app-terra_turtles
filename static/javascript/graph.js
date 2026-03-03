/* graph.js
 */
(async function () {
  new Chart(document.getElementById("calories"), {
    type: "line",
    data: {
      labels: caloriesData.map((item) => {
        const [year, month, day] = item.date.split("-");
        const months = [
          "Jan",
          "Feb",
          "Mar",
          "Apr",
          "May",
          "Jun",
          "Jul",
          "Aug",
          "Sep",
          "Oct",
          "Nov",
          "Dec",
        ];
        return months[parseInt(month) - 1] + " " + parseInt(day);
      }),
      datasets: [
        {
          data: caloriesData.map((item) => item.calories),
          tension: 0.25,
          pointRadius: 0,
        },
      ],
    },
    options: {
      plugins: {
        legend: {
          display: false,
        },
      },
      scales: {
        x: {
          ticks: {
            maxTicksLimit: 10,
          },
        },
      },
    },
  });
})();
