export const config = {
  matcher: ['/', '/posts/:path*'],
}

export default function middleware(request) {
  const accept = request.headers.get('accept') || ''

  if (accept.includes('text/markdown')) {
    const url = new URL(request.url)
    // Rewrite to markdown file
    if (url.pathname === '/') {
      url.pathname = '/index.md'
    } else {
      url.pathname = url.pathname.replace(/\/?$/, '/index.md')
    }
    return Response.redirect(url, 302)
  }
}
