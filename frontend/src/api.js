import axios from "axios";

export const searchVideos = async (query) => {
  const res = await axios.get(
    `http://localhost:5000/api/search?q=${encodeURIComponent(query)}`
  );
  return res.data;
};