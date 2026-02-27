import axios from "axios";

const baseURL = "http://localhost:8888/api/v1/modular";

export const api = axios.create({
  baseURL,
});

export const getSensors = () => api.get("/sensors").then((res) => res.data);
export const getWidgets = () => api.get("/widgets").then((res) => res.data);
export const getScreens = () => api.get("/screens").then((res) => res.data);
export const getThemes = () => api.get("/themes").then((res) => res.data);
export const getSettings = () => api.get("/settings").then((res) => res.data);

export const addSensor = (data) =>
  api.post("/sensors", data).then((res) => res.data);
export const addWidget = (data) =>
  api.post("/widgets", data).then((res) => res.data);
export const addScreen = (data) =>
  api.post("/screens", data).then((res) => res.data);
export const addTheme = (data) =>
  api.post("/themes", data).then((res) => res.data);

export const deleteSensor = (id) =>
  api.delete(`/sensors/${id}`).then((res) => res.data);
export const deleteWidget = (id) =>
  api.delete(`/widgets/${id}`).then((res) => res.data);
export const deleteScreen = (id) =>
  api.delete(`/screens/${id}`).then((res) => res.data);
export const deleteTheme = (id) =>
  api.delete(`/themes/${id}`).then((res) => res.data);

export const activateTheme = (id) =>
  api.post(`/active_theme/${id}`).then((res) => res.data);
export const updateSettings = (data) =>
  api.post("/settings", data).then((res) => res.data);
