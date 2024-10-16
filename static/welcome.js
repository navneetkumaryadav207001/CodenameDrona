let tl = gsap.timeline();

tl.from("#header",{
    // delay:1,
    y:-200,
    duration:0.5,
    scrub:3
})
tl.from("#headerImage img",{
    y:-30,
    opacity:0,
    duration:0.5
})

tl.from(".options",{
    y:-30,
    opacity:0,
    stagger:0.5,
    duration:0.5,
    scrub:3,
    stagger:2
},"-=0.2")

tl.from("#homeOptions h1",{
    x:-50,
    opacity:0,
    duration:0.8
})

tl.from("#homeOptions p",{
    x:50,
    opacity:0,
    duration:0.8
},"-=0.5")

tl.from("#homeImage img",{
    x:200,
    opacity:0,
    duration:0.8,
    scrub:2
},"-=0.5")

gsap.from("#aboutDrona",{
    scale:1.5,
    x:-300,
    opacity:0,
    duration:0.5,
    scrollTrigger:{
        scroller:"body",
        trigger:"#aboutContainer",
        start:"top 50%",
        end:"top 70%",
        scrub:3
    }
})

gsap.from("#aboutImage img",{
    scale:1.5,
    x:300,
    opacity:0,
    duration:0.5,
    scrollTrigger:{
        scroller:"body",
        trigger:"#aboutContainer",
        start:"top 50%",
        end:"top 70%",
        scrub:3
    }
})
