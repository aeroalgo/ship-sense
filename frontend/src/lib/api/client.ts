import type { ApiErrorBody } from "./types";

export class ApiError extends Error {
  readonly status: number;
  readonly code: string;
  readonly details: unknown;

  constructor(
    status: number,
    code: string,
    message: string,
    details?: unknown,
  ) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
    this.details = details;
  }
}

export type ApiResult<T> = {
  data: T;
  headers: Headers;
  status: number;
};

export type QueryValue =
  | string
  | number
  | boolean
  | null
  | undefined
  | ReadonlyArray<string | number | boolean>;

export type ApiRequestOptions = {
  query?: Record<string, QueryValue>;
  headers?: HeadersInit;
  signal?: AbortSignal;
  body?: unknown;
};

export function joinApiUrl(base: string, path: string): string {
  const normalizedBase = base.replace(/\/+$/, "");
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  return `${normalizedBase}${normalizedPath}`;
}

export function getApiBaseUrl(): string {
  const base = process.env.NEXT_PUBLIC_API_URL;
  if (!base) {
    throw new Error("NEXT_PUBLIC_API_URL is not set");
  }
  return base.replace(/\/+$/, "");
}

export function buildQueryString(
  query: Record<string, QueryValue> | undefined,
): string {
  if (!query) return "";
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(query)) {
    if (value === undefined || value === null) continue;
    if (Array.isArray(value)) {
      for (const item of value) {
        params.append(key, String(item));
      }
      continue;
    }
    params.append(key, String(value));
  }
  const qs = params.toString();
  return qs ? `?${qs}` : "";
}

type UnauthorizedListener = (error: ApiError) => void;

const unauthorizedListeners = new Set<UnauthorizedListener>();

export function onUnauthorized(listener: UnauthorizedListener): () => void {
  unauthorizedListeners.add(listener);
  return () => {
    unauthorizedListeners.delete(listener);
  };
}

export function notifyUnauthorized(error: ApiError): void {
  for (const listener of unauthorizedListeners) {
    listener(error);
  }
}

async function parseApiError(response: Response): Promise<ApiError> {
  let body: ApiErrorBody | undefined;
  try {
    body = (await response.json()) as ApiErrorBody;
  } catch {
    body = undefined;
  }
  const envelope = body?.error;
  if (envelope && typeof envelope.code === "string") {
    return new ApiError(
      response.status,
      envelope.code,
      envelope.message ?? response.statusText,
      envelope.details,
    );
  }
  return new ApiError(
    response.status,
    "HTTP_ERROR",
    response.statusText || `HTTP ${response.status}`,
  );
}

async function request<T>(
  method: string,
  path: string,
  options: ApiRequestOptions = {},
): Promise<ApiResult<T>> {
  const url =
    joinApiUrl(getApiBaseUrl(), path) + buildQueryString(options.query);
  const headers = new Headers(options.headers);
  if (options.body !== undefined && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json; charset=utf-8");
  }

  const response = await fetch(url, {
    method,
    credentials: "include",
    headers,
    signal: options.signal,
    body:
      options.body === undefined ? undefined : JSON.stringify(options.body),
  });

  if (!response.ok) {
    const error = await parseApiError(response);
    if (error.status === 401) {
      notifyUnauthorized(error);
    }
    throw error;
  }

  if (response.status === 204) {
    return { data: undefined as T, headers: response.headers, status: 204 };
  }

  const contentType = response.headers.get("content-type") ?? "";
  if (contentType.includes("text/html")) {
    const html = await response.text();
    return { data: html as T, headers: response.headers, status: response.status };
  }

  const data = (await response.json()) as T;
  return { data, headers: response.headers, status: response.status };
}

export function apiGet<T>(
  path: string,
  options?: ApiRequestOptions,
): Promise<ApiResult<T>> {
  return request<T>("GET", path, options);
}

export function apiPost<T>(
  path: string,
  body?: unknown,
  options?: Omit<ApiRequestOptions, "body">,
): Promise<ApiResult<T>> {
  return request<T>("POST", path, { ...options, body });
}

export function apiDelete(
  path: string,
  options?: ApiRequestOptions,
): Promise<ApiResult<void>> {
  return request<void>("DELETE", path, options);
}
