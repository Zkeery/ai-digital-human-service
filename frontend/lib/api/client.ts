export type ApiErrorBody = {
  error: { code: string; message: string };
};

export class ApiError extends Error {
  code: string;
  status: number;

  constructor(status: number, code: string, message: string) {
    super(message);
    this.status = status;
    this.code = code;
  }
}

export function apiBase(): string {
  return process.env.NEXT_PUBLIC_API_BASE?.replace(/\/$/, "") || "http://127.0.0.1:8050";
}

export async function apiJson<T>(
  path: string,
  init?: RequestInit,
): Promise<T> {
  const res = await fetch(`${apiBase()}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers || {}),
    },
  });
  const text = await res.text();
  let data: unknown = null;
  try {
    data = text ? JSON.parse(text) : null;
  } catch {
    data = { raw: text };
  }
  if (!res.ok) {
    const err = data as ApiErrorBody;
    const code = err?.error?.code || "HTTP_ERROR";
    const message = err?.error?.message || `请求失败（${res.status}）`;
    throw new ApiError(res.status, code, message);
  }
  return data as T;
}
