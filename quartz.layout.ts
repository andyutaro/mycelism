import { PageLayout, SharedLayout } from "./quartz/cfg"
import * as Component from "./quartz/components"

const graphOptions = {
  localGraph: {
    drag: true,
    zoom: true,
    depth: 1,
    scale: 1.05,
    repelForce: 1.15,
    centerForce: 0.18,
    linkDistance: 120,
    fontSize: 0.75,
    opacityScale: 1,
  },
  globalGraph: {
    drag: true,
    zoom: true,
    depth: -1,
    scale: 0.88,
    repelForce: 0.05,
    centerForce: 1.0,
    linkDistance: 5,
    fontSize: 0.6,
    opacityScale: 1,
    showTags: false,
    focusOnHover: true,
    enableRadial: false,
  },
}

const explorerOptions = {
  folderClickBehavior: "collapse" as const,
  folderDefaultState: "collapsed" as const,
  useSavedState: true,
  filterFn: (node: any) => {
    return node.name !== "concepts"
  },
  sortFn: (a: any, b: any) => {
    if (!a.isFolder && b.isFolder) return 1
    if (a.isFolder && !b.isFolder) return -1
    if (a.isFolder && b.isFolder) {
      return a.displayName.localeCompare(b.displayName, undefined, {
        numeric: true,
        sensitivity: "base",
      })
    }
    const aDate = a.data?.date ? new Date(a.data.date) : new Date(0)
    const bDate = b.data?.date ? new Date(b.data.date) : new Date(0)
    return bDate.getTime() - aDate.getTime()
  },
  mapFn: (node: any) => {
    if (node.file && node.data) {
      const m = (node.data.slug ?? "").match(/\/(\d{4}-\d{2}-\d{2})-/)
      if (m) node.data.date = new Date(m[1])
    }
    return node
  },
}

export const sharedPageComponents: SharedLayout = {
  head: Component.Head(),
  header: [],
  afterBody: [],
  footer: Component.Footer(),
}

export const defaultContentPageLayout: PageLayout = {
  beforeBody: [
    Component.Breadcrumbs(),
    Component.ArticleTitle(),
    Component.ContentMeta(),
  ],
  left: [
    Component.PageTitle(),
    Component.Search(),
    Component.Darkmode(),
    Component.DesktopOnly(Component.Explorer(explorerOptions)),
  ],
  right: [
    Component.Graph(graphOptions),
    Component.DesktopOnly(Component.TableOfContents()),
    Component.Backlinks(),
  ],
}

export const defaultListPageLayout: PageLayout = {
  beforeBody: [
    Component.Breadcrumbs(),
    Component.ArticleTitle(),
    Component.ContentMeta(),
  ],
  left: [
    Component.PageTitle(),
    Component.Search(),
    Component.Darkmode(),
    Component.DesktopOnly(Component.Explorer(explorerOptions)),
  ],
  right: [
    Component.Graph(graphOptions),
    Component.DesktopOnly(Component.TableOfContents()),
  ],
}
