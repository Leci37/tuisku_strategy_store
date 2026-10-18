// Pinta un trozo de la página en otro sitio del documento (los huecos de la barra del núcleo), con el
// mismo estado: el Portal de preact/compat, para el que el núcleo de Preact sólo necesita render().
import { Component, Fragment, h, render } from '../../vendor/preact.module.js';

export class Portal extends Component {
  componentDidMount() { this.paint(); }
  componentDidUpdate() { this.paint(); }
  componentWillUnmount() { if (this.props.into) render(null, this.props.into); }
  paint() { if (this.props.into) render(h(Fragment, null, this.props.children), this.props.into); }
  render() { return null; }
}
