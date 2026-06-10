import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
  // Day 7 收口修复：启用 standalone 输出模式
  // Dockerfile 需要 COPY /app/.next/standalone，必须配置此选项才能生成该目录
  // 参考：https://nextjs.org/docs/app/api-reference/config/next-config-js/output
  output: "standalone",
};

export default nextConfig;
