// Structured service failures never surface raw server JSON to the user.
function rateLimitMessage(seconds) {
  const minutes = Math.max(1, Math.ceil(seconds / 60));
  return uiText(
    `Too many requests. Please try again in about ${minutes} minute(s).`,
    `طلبات كثيرة. حاول مجدداً خلال نحو ${minutes} دقيقة.`,
  );
}
function checkServiceResponse(response) {
  if (response.status !== 429) return;
  const error = new Error("rate_limited"),
    retry = Number(response.headers.get("Retry-After"));
  error.retrySeconds = Number.isFinite(retry) && retry > 0 ? retry : 60;
  throw error;
}
function showRateLimit(id, seconds) {
  const minutes = Math.max(1, Math.ceil(seconds / 60));
  localizedStatus(
    id,
    `Too many requests. Please try again in about ${minutes} minute(s).`,
    `طلبات كثيرة. حاول مجدداً خلال نحو ${minutes} دقيقة.`,
  );
}
