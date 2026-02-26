import axios from "axios";


const rawUrl = import.meta.env.VITE_API_URL ?? "";
const baseHost = rawUrl.replace(/\/+$/g, ""); // remove trailing slash(es)
const baseURL = (baseHost || "") + "/api";



// export default axios instance instead of named export
const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL + "/api",
});

export default api;
