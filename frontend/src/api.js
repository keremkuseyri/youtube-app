import axios from "axios";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, "") || "http://localhost:5000";

export const searchVideos = async (query) => {
  const res = await axios.get(
    `${API_BASE_URL}/api/search?q=${encodeURIComponent(query)}`
  );
  return res.data;
};