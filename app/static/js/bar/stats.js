// Retrieve data
var data = document.getElementById("data-storage");
var labels = data.dataset["daysLabels"];
var clients = data.dataset["clientsThisMonth"];
var clientsAlcohol = data.dataset["clientsAlcoholThisMonth"];
var revenues = data.dataset["revenuesThisMonth"];

// Theme detection
const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
const textColor = isDark ? '#94a3b8' : '#64748b';
const titleColor = isDark ? '#f8fafc' : '#1e293b';
const gridColor = isDark ? 'rgba(255, 255, 255, 0.08)' : 'rgba(0, 0, 0, 0.05)';

// Global defaults for modern themes
Chart.defaults.color = textColor;
Chart.defaults.font.family = "'Inter', system-ui, -apple-system, sans-serif";

// Define the chart data
var chartDataMonth = {
  labels: labels.split(","),
  datasets: [
    {
      label: "Total",
      fill: false,
      backgroundColor: "#ef4444",
      borderColor: "#ef4444",
      data: clients.split(","),
      tension: 0,
      pointRadius: 4,
      pointHoverRadius: 6,
    },
    {
      label: "Alcohol",
      fill: false,
      backgroundColor: "#3b82f6",
      borderColor: "#3b82f6",
      data: clientsAlcohol.split(","),
      tension: 0,
      pointRadius: 4,
      pointHoverRadius: 6,
    },
  ],
};

// Transactions Chart
var ctx = document.querySelector("#transactions-chart").getContext("2d");
var transactionsChart = new Chart(ctx, {
  type: "line",
  data: chartDataMonth,
  options: {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        labels: {
          color: textColor,
          usePointStyle: true,
          padding: 20,
        }
      },
      tooltip: {
        mode: "index",
        intersect: false,
        backgroundColor: isDark ? '#0f172a' : '#ffffff',
        titleColor: isDark ? '#f8fafc' : '#1e293b',
        bodyColor: isDark ? '#e2e8f0' : '#475569',
        borderColor: isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)',
        borderWidth: 1,
        padding: 12,
      }
    },
    scales: {
      x: {
        grid: { color: gridColor, drawBorder: false },
        ticks: { color: textColor, padding: 10 },
        title: {
          display: true,
          text: "Day",
          color: textColor
        },
      },
      y: {
        grid: { color: gridColor, drawBorder: false },
        ticks: { 
          color: textColor,
          padding: 10,
          callback: function (value) { if (Number.isInteger(value)) { return value; } }
        },
        title: {
          display: true,
          text: "Clients",
          color: textColor
        },
      },
    },
  },
});

var chartMoulaMonth = {
  labels: labels.split(","),
  datasets: [
    {
      label: "Moula",
      backgroundColor: "#ef4444",
      borderColor: "#ef4444",
      data: revenues.split(","),
      borderRadius: 2,
    },
  ],
};

// Revenues Chart
var ctx2 = document.querySelector("#revenues-chart").getContext("2d");
var revenuesChart = new Chart(ctx2, {
  type: "bar",
  data: chartMoulaMonth,
  options: {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        labels: {
          color: textColor,
          usePointStyle: true,
          padding: 20,
        }
      },
      tooltip: {
        backgroundColor: isDark ? '#0f172a' : '#ffffff',
        titleColor: isDark ? '#f8fafc' : '#1e293b',
        bodyColor: isDark ? '#e2e8f0' : '#475569',
        borderColor: isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)',
        borderWidth: 1,
        padding: 12,
      }
    },
    scales: {
      x: {
        grid: { display: false },
        ticks: { color: textColor, padding: 10 },
        title: {
          display: true,
          text: "Day",
          color: textColor
        },
      },
      y: {
        grid: { color: gridColor, drawBorder: false },
        ticks: { color: textColor, padding: 10 },
        title: {
          display: true,
          text: "Moula (in €)",
          color: textColor
        },
      },
    },
  },
});
