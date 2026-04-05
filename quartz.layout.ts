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
    repelForce: 1.75,
    centerForce: 0.04,
    linkDistance: 185,
    fontSize: 0.7,
    opacityScale: 1,
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
    Component.Explorer(),
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
    Component.Explorer(),
  ],
  right: [
    Component.Graph(graphOptions),
    Component.DesktopOnly(Component.TableOfContents()),
  ],
}
