import { QuartzComponent, QuartzComponentConstructor, QuartzComponentProps } from "./types"
import * as Component from "./index"

const heroGraphOptions = {
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

export default (() => {
  const GraphComponent = Component.Graph(heroGraphOptions)

  const HeroGraph: QuartzComponent = (props: QuartzComponentProps) => {
    if (props.fileData.slug !== "index") {
      return null
    }

    return (
      <div class="hero-graph">
        <GraphComponent {...props} />
      </div>
    )
  }

  return HeroGraph
}) satisfies QuartzComponentConstructor
