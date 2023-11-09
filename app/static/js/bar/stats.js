// Retrieve data
var data = document.getElementById("data-storage");
var labels = data.dataset["daysLabels"];
var clients = data.dataset["clientsThisMonth"];
var clientsAlcohol = data.dataset["clientsAlcoholThisMonth"];
var revenues = data.dataset["revenuesThisMonth"];

// Global parameters:
// Chart.defaults.global.responsive = true;

// Define the chart data
var chartDataMonth = {
  labels: labels.split(","),
  datasets: [
    {
      label: "Total",
      fill: false,
      backgroundColor: "#dc3545",
      borderColor: "#dc3545",
      data: clients.split(","),
    },
    {
      label: "Alcohol",
      fill: false,
      backgroundColor: "#007bff",
      borderColor: "#007bff",
      data: clientsAlcohol.split(","),
    },
  ],
};

// Get chart canvas
var ctx = document.querySelector("#transactions-chart").getContext("2d");
// Create the chart using the chart canvas
var transactionsChart = new Chart(ctx, {
  type: "line",
  data: chartDataMonth,
  options: {
    responsive: true,
    maintainAspectRatio: false,
    tooltips: {
      mode: "index",
      intersect: false,
    },
    hover: {
      mode: "nearest",
      intersect: true,
    },
    scales: {
      x:
        {
          display: true,
          title: {
            display: true,
            text: "Day",
          },
        },
      y: 
        {
          display: true,
          title: {
            display: true,
            text: "Clients",
          },
          ticks: {
            callback: function (value) { if (Number.isInteger(value)) { return value; } },
        }
        },
    },
  },
});

var chartMoulaMonth = {
  labels: labels.split(","),
  datasets: [
    {
      label: "Moula",
      fill: false,
      backgroundColor: "#dc3545",
      borderColor: "#dc3545",
      data: revenues.split(","),
    },
  ],
};
// Get chart canvas
var ctx = document.querySelector("#revenues-chart").getContext("2d");
// Create the chart using the chart canvas
var revenuesChart = new Chart(ctx, {
  type: "bar",
  data: chartMoulaMonth,
  options: {
    responsive: true,
    maintainAspectRatio: false,
    tooltips: {
      mode: "index",
      intersect: false,
    },
    hover: {
      mode: "nearest",
      intersect: true,
    },
    scales: {
      x:
        {
          display: true,
          title: {
            display: true,
            text: "Day",
          },
        },
      y:
        {
          display: true,
          title: {
            display: true,
            text: "Moula (in €)",
          },
        },
    },
  },
});
