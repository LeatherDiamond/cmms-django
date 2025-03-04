$(document).ready(function() {
    let footer_node = document.querySelector('.footer');
    if (footer_node) {
        footer_node.classList.add("visible");
        new Footer(footer_node);
    }
    
});


class Footer {

    constructor (footer_node=null) {
        if(!footer_node) {
            console.error('footer not found');
            return null;
        }
        this.footer_node = footer_node;
        this.footer_p_height = footer_node.querySelector('p').offsetHeight;
        this.translate_value = null;
        this.footer_node.style.bottom = `${-this.footer_p_height}px`;
        this.add_events();
    }

    add_events() {
        window.addEventListener("resize", () => {
            this.footer_p_height = this.footer_node.querySelector('p').offsetHeight;
            this.translate_value = null;
            this.footer_node.style.bottom = `${-this.footer_p_height}px`;
            this.footer_node.style.transform = `translateY(0px)`;
        });
        this.footer_node.querySelector('.footer-toggler-button').addEventListener("click", evt => {
            this.translate_value = this.translate_value ? 0 : -this.footer_p_height;
            this.footer_node.style.transform = `translateY(${this.translate_value}px)`;
        });
    }
}
