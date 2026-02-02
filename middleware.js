export const config = {
  matcher: ['/', '/posts/:path*'],
}

export default async function middleware(request) {
  const accept = request.headers.get('accept') || ''

  if (accept.includes('text/markdown')) {
    const url = new URL(request.url)
    // Rewrite to markdown file (no redirect)
    if (url.pathname === '/') {
      url.pathname = '/index.md'
    } else {
      url.pathname = url.pathname.replace(/\/?$/, '/index.md')
    }
    // Fetch and return the markdown file directly
    return fetch(url)
  }
}
