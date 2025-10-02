import { useEffect, useState } from "react";
import { apiGet } from "@/lib/api";

export function useMyCourses() {
  const [courses, setCourses] = useState<any[]>([]);
  useEffect(() => {
    apiGet("/courses/my").then((d) => setCourses(d.courses || []));
  }, []);
  return courses;
}

