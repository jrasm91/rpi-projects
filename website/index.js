const hostname = window.location.host || '127.0.0.1:6789';
const url = `ws://${hostname}/ws`;
console.log(`URL: ${url}`);

function dayPipe(value) {
  if (!value) {
    return '';
  }
  if (typeof value === 'string') {
    value = value.replace(/-/, '/');
  }
  return new Date(value).toLocaleDateString();
}

function timePipe(value) {
  if (!value) {
    return '';
  }
  if (typeof value === 'string') {
    value = value.replace(/-/, '/');
  }
  let [time, ampm] = new Date(value).toLocaleTimeString().split(' ');
  return [time.substr(0, time.length - 3), ampm].join(' ');
}

Vue.filter('dayPipe', dayPipe);

Vue.filter('timePipe', timePipe);

const _expanded = {};

let websocket = null;
const app = new Vue({
  el: '#app',
  data: {
    today: new Date(),
    loading: false,
    zones: [],
    waterHistory: [],
    activeTab: 'zones',
    scheduled: [],
    sunset: null,
    sunrise: null,
    sunsetHistory: [],
    connected: false,
  },
  created: function () {
    this.connect();
    this.interval = setInterval(() => this.handleRefresh(), 5000);
  },
  methods: {
    connect: function () {
      const websocket = new WebSocket(url);
      websocket.onopen = () => (this.connected = true);
      websocket.onclose = () => (this.connected = false);
      websocket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === 'connect') {
          this.onConnect(data);
        }
        if (data.type === 'refresh') {
          this.onRefresh(data);
        }
      };
      this.websocket = websocket;
    },
    handleRefresh: function () {
      this.today = new Date();
      if (!this.connected) {
        this.connect();
      } else {
        this._notify({ action: 'refresh' });
      }
    },
    handleSchedule: function (zone, value) {
      this.loading = true;
      this._notify({ action: 'schedule_zone', valve: zone.valve, value });
    },
    handleStart: function (zone) {
      this.loading = true;
      this._notify({ action: 'open_valve', valve: zone.valve });
    },
    handleStop: function (zone) {
      this.loading = true;
      this._notify({ action: 'close_valve', valve: zone.valve });
    },
    handleAdjustOverride: function (zone, value) {
      this.loading = true;
      this._notify({ action: 'adjust_zone_override', valve: zone.valve, value });
    },
    handleAdjustScheduledDuration: function (item, value) {
      this.loading = true;
      this._notify({ action: 'adjust_scheduled_duration', id: item.id, value });
    },
    handleCancelScheduled: function (item) {
      this.loading = true;
      this._notify({ action: 'cancel_scheduled_item', id: item.id });
    },
    handleToggle: function (item) {
      const key = item._key;
      item._expanded = _expanded[key] = !_expanded[key];
    },
    onConnect: function (data) {
      const monthNames = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];
      let todayMonth = monthNames[new Date().getMonth()];
      let todayDay = dayPipe(new Date());
      let currentMonth = null;
      let list = [];
      for (let [sunrise, sunset] of data.sunset_history || []) {
        const monthName = monthNames[new Date(sunrise).getMonth()];
        if (!currentMonth || monthName !== currentMonth.month) {
          currentMonth = { month: monthName, items: [] };
          list.push(currentMonth);
          const key = `month.${monthName}`;
          currentMonth._key = key;
          currentMonth._expanded = _expanded[key];
          currentMonth.active = monthName === todayMonth;
        }
        currentMonth.items.push({ sunset, sunrise, active: todayDay === dayPipe(sunset) });
      }
      this.sunsetHistory = list;
    },
    onRefresh: function (data) {
      this.loading = false;
      this.waterHistory = [];
      this.scheduled = [];

      this.sunrise = data.sunrise;
      this.sunset = data.sunset;

      data.water_history = (data.water_history || []).sort((a, b) => {
        date1 = new Date(a.actual_start || a.scheduled_start);
        date2 = new Date(b.actual_start || b.scheduled_start);
        return date1 === date2 ? 0 : date1 > date2 ? -1 : 1;
      });

      function reducer({ currentDay, list, states }, history) {
        if (states.find((state) => state === history.state)) {
          const day = dayPipe(history.actual_start || history.scheduled_start);
          if (!currentDay || day !== currentDay.day) {
            currentDay = { day, items: [] };
            list.push(currentDay);
          }
          currentDay.items.push(history);
        }
        return { currentDay, list, states };
      }

      for (let history of data.water_history || []) {
        const key = `history.${history.id}`;
        history._key = key;
        history._expanded = !!_expanded[key];
      }

      this.waterHistory = (data.water_history || []).reduce(reducer, { states: ['done', 'cancelled'], list: [] }).list;
      this.scheduled = (data.water_history || []).reduce(reducer, { states: ['pending', 'active'], list: [] }).list;

      for (let zone of data.zones || []) {
        const key = `zone.${zone.valve}`;
        zone._key = key;
        zone._expanded = !!_expanded[key];
      }

      const enabled = [];
      const disabled = [];
      for (let zone of data.zones || []) {
        (zone.is_enabled ? enabled : disabled).push(zone);
      }
      this.zones = enabled; // [...enabled, ...disabled];
    },
    _notify: function (message) {
      if (!this.connected) {
        console.warn('Unable to send message, websocket is disconnected.');
        return;
      }
      message = JSON.stringify(message);
      this.websocket.send(message);
    },
  },
});
